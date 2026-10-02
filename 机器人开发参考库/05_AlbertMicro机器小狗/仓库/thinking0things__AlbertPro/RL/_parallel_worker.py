
"""
_parallel_worker.py
Subprocess worker for parallel PPO experience collection.
Receives current policy weights + config, runs one episode, returns transitions.
"""
import os, math
import numpy as np
import torch
import torch.nn as nn
import mujoco


def _worker(worker_id: int, weights_numpy: dict, cfg: dict) -> dict:
    """
    Collect one episode of experience in an independent MuJoCo instance.

    Parameters
    ----------
    worker_id     : int  — used for seeding / debugging
    weights_numpy : dict[str, ndarray] — current policy weights as numpy arrays
    cfg           : dict — all hyperparameters (see build_cfg() in the notebook)

    Returns
    -------
    dict with lists: states, actions, log_probs, rewards, values, dones
         and scalars: last_value, dist, tot_r
    """
    # ── Unpack config ────────────────────────────────────────────────────────
    STATE_DIM    = cfg["STATE_DIM"]
    ACTION_DIM   = cfg["ACTION_DIM"]
    HIDDEN_DIM   = cfg["HIDDEN_DIM"]
    LOG_STD_INIT = cfg["LOG_STD_INIT"]
    LOG_STD_MIN  = cfg["LOG_STD_MIN"]
    LOG_STD_MAX  = cfg["LOG_STD_MAX"]

    SUBSTEPS     = cfg["SUBSTEPS"]
    SETTLE_TIME  = cfg["SETTLE_TIME"]
    EPISODE_DUR  = cfg["EPISODE_DUR"]
    XML_PATH     = cfg["XML_PATH"]

    HIP_INIT     = cfg["HIP_INIT"]
    KNEE_INIT    = cfg["KNEE_INIT"]
    DELTA_HIP    = cfg["DELTA_HIP"]
    DELTA_KNEE   = cfg["DELTA_KNEE"]
    MAX_DDELTA   = cfg["MAX_DDELTA"]
    DELTA_LIMIT  = cfg["DELTA_LIMIT"]

    TARGET_VX    = cfg["TARGET_VX"]
    VX_TRACK_W   = cfg["VX_TRACK_W"]
    VX_TOL       = cfg["VX_TOL"]
    ALIVE_BONUS  = cfg["ALIVE_BONUS"]
    JVEL_W       = cfg["JVEL_W"]
    JEXC_W       = cfg["JEXC_W"]
    ACTION_REG_W = cfg["ACTION_REG_W"]
    DELTA_REG_W  = cfg["DELTA_REG_W"]
    ALIGN_W      = cfg["ALIGN_W"]
    YAW_W        = cfg["YAW_W"]

    OFFSETS  = np.array([HIP_INIT, KNEE_INIT] * 4, dtype=np.float32)
    JOINT_LO = np.array([HIP_INIT - DELTA_HIP,  KNEE_INIT - DELTA_KNEE] * 4, dtype=np.float32)
    JOINT_HI = np.array([HIP_INIT + DELTA_HIP,  KNEE_INIT + DELTA_KNEE] * 4, dtype=np.float32)

    # ── Each subprocess gets its own MuJoCo instance ─────────────────────────
    # MuJoCo model/data are not serialisable — must be created fresh per process.
    mjmodel = mujoco.MjModel.from_xml_path(XML_PATH)
    mjdata  = mujoco.MjData(mjmodel)
    CTRL_DT = mjmodel.opt.timestep * SUBSTEPS

    # ── Reconstruct ActorCritic from transmitted weights ──────────────────────
    # We define the class inline so the worker file is fully self-contained.
    class ActorCritic(nn.Module):
        def __init__(self):
            super().__init__()
            self.pi = nn.Sequential(
                nn.Linear(STATE_DIM, HIDDEN_DIM), nn.ReLU(),
                nn.Linear(HIDDEN_DIM, ACTION_DIM),
            )
            self.log_std = nn.Parameter(torch.full((ACTION_DIM,), LOG_STD_INIT))
            self.vf = nn.Sequential(
                nn.Linear(STATE_DIM, 256), nn.ReLU(),
                nn.Linear(256, 256),       nn.ReLU(),
                nn.Linear(256, 1),
            )

        def get_action(self, s):
            mean    = self.pi(s)
            log_std = self.log_std.clamp(LOG_STD_MIN, LOG_STD_MAX)
            std     = log_std.exp()
            raw     = mean + std * torch.randn_like(std)
            action  = torch.tanh(raw)
            log_prob = (-0.5 * ((raw - mean) / (std + 1e-8))**2
                        - log_std - 0.5 * math.log(2 * math.pi))
            log_prob -= torch.log(1 - action.pow(2) + 1e-6)
            log_prob  = log_prob.sum(-1)
            value = self.vf(s).squeeze(-1)
            return action, log_prob, value

    ac = ActorCritic()
    # Convert numpy arrays back to tensors and load
    state_dict = {k: torch.from_numpy(v) for k, v in weights_numpy.items()}
    ac.load_state_dict(state_dict)
    ac.eval()

    # ── Simulation helpers ────────────────────────────────────────────────────
    def orientation():
        qw, qx, qy, qz = mjdata.qpos[3:7]
        roll  = math.atan2(2*(qw*qx + qy*qz), 1 - 2*(qx**2 + qy**2))
        pitch = math.asin(float(np.clip(2*(qw*qy - qz*qx), -1, 1)))
        yaw   = math.atan2(2*(qw*qz + qx*qy), 1 - 2*(qy**2 + qz**2))
        return roll, pitch, yaw

    def build_state(delta):
        return np.concatenate([
            mjdata.qpos[7:15].astype(np.float32),
            mjdata.qvel[6:14].astype(np.float32),
            delta.astype(np.float32),
        ])

    def apply_ddelta(ctrl, delta, ddelta):
        delta_new = np.clip(delta + ddelta * MAX_DDELTA, -DELTA_LIMIT, DELTA_LIMIT)
        ctrl_new  = np.clip(ctrl  + delta_new, JOINT_LO, JOINT_HI)
        return ctrl_new, delta_new

    def is_done():
        _, p, _ = orientation()
        return mjdata.qpos[2] < 0.03 or abs(p) > math.radians(45)

    def reset_sim():
        ip = np.array([HIP_INIT, KNEE_INIT] * 4, dtype=np.float32)
        mujoco.mj_resetData(mjmodel, mjdata)
        mjdata.qpos[7:15] = ip
        mjdata.qpos[2]    = 0.10
        mujoco.mj_forward(mjmodel, mjdata)
        for _ in range(int(SETTLE_TIME / mjmodel.opt.timestep)):
            mjdata.ctrl[:] = ip
            mujoco.mj_step(mjmodel, mjdata)
        return ip.copy(), np.zeros(ACTION_DIM, dtype=np.float32)

    # ── Rollout ───────────────────────────────────────────────────────────────
    ctrl, delta = reset_sim()
    x0          = mjdata.qpos[0]
    _, _, yaw0  = orientation()
    tot_r       = 0.0
    s           = build_state(delta)

    states, actions, log_probs, rewards, values, dones = [], [], [], [], [], []

    done = False
    for _ in range(int(EPISODE_DUR / CTRL_DT)):
        st = torch.FloatTensor(s).unsqueeze(0)
        with torch.no_grad():
            action, log_prob, value = ac.get_action(st)
        an = action.squeeze(0).numpy()
        lp = log_prob.item()
        v  = value.item()

        ctrl, delta = apply_ddelta(ctrl, delta, an)
        mjdata.ctrl[:] = ctrl
        for _ in range(SUBSTEPS):
            mujoco.mj_step(mjmodel, mjdata)

        roll, pitch, yaw = orientation()
        dyaw     = (yaw - yaw0 + math.pi) % (2 * math.pi) - math.pi
        vx       = float(mjdata.qvel[0])
        vy       = abs(float(mjdata.qvel[1]))
        jvel_mag = float(np.mean(np.abs(mjdata.qvel[6:14])))
        jpos     = mjdata.qpos[7:15].astype(np.float32)
        excursion = float(np.mean(np.abs(jpos - OFFSETS)))

        vx_err = max(0.0, abs(vx - TARGET_VX) - VX_TOL)
        r = (-VX_TRACK_W * vx_err**2
             + ALIVE_BONUS
             - 0.10 * vy
             - ACTION_REG_W * float(np.sum(an**2))
             - DELTA_REG_W  * float(np.sum(delta**2))
             + JVEL_W       * jvel_mag
             + JEXC_W       * excursion
             - ALIGN_W      * (roll**2 + pitch**2)
             - YAW_W        * dyaw**2)
        tot_r += r
        done = is_done()
        if done:
            r -= 5.0

        states.append(s); actions.append(an)
        log_probs.append(lp); rewards.append(r)
        values.append(v); dones.append(float(done))
        s = build_state(delta)
        if done:
            break

    if done:
        last_value = 0.0
    else:
        with torch.no_grad():
            last_value = ac.vf(torch.FloatTensor(s).unsqueeze(0)).squeeze().item()

    return {
        "states":     states,
        "actions":    actions,
        "log_probs":  log_probs,
        "rewards":    rewards,
        "values":     values,
        "dones":      dones,
        "last_value": last_value,
        "dist":       mjdata.qpos[0] - x0,
        "tot_r":      tot_r,
    }
