"""Music playback for a smart speaker.

The split that matters: play_music starts named content, and the zero-argument
playback tools control whatever is already playing. Volume is the only number,
and it is bounded.
"""

import os
from typing import Annotated

os.environ.setdefault("NEEDLE_STRICT_VALIDATE", "1")
import needle


@needle.tool
def play_music(query: Annotated[str, needle.Field(min_length=1, max_length=80)]):
    """Play music by song name, artist, album, or genre. Copy the request word for word. Use the playback tools for pausing, resuming, or skipping.

    Args:
        query: The song, artist, album, or genre, copied word for word.
    """
    return {"ok": True, "query": query}


@needle.tool
def pause_media():
    """Pause the currently playing media. Takes no arguments."""
    return {"ok": True, "state": "paused"}


@needle.tool
def resume_media():
    """Resume the paused media playback. Starting something new is play_music. Takes no arguments."""
    return {"ok": True, "state": "playing"}


@needle.tool
def skip_track():
    """Skip to the next track. Takes no arguments."""
    return {"ok": True, "state": "skipped"}


@needle.tool
def set_volume(level: Annotated[int, needle.Field(ge=0, le=100)]):
    """Set the speaker volume. This never pauses or skips anything.

    Args:
        level: Volume level from 0 to 100.
    """
    return {"ok": True, "level": level}


TOOLS = [play_music, pause_media, resume_media, skip_track, set_volume]
agent = needle.Needle(
    tools=TOOLS,
    system="Map each explicit supported media action to exactly one declared call; never duplicate an action. Do not guess missing values. Unsupported, invalid, ambiguous, and negated requests return no call.",
)


TEST_CASES = [
    {'query': 'play Purple Rain by Prince', 'calls': [{'name': 'play_music', 'arguments': {'query': 'Purple Rain by Prince'}}], 'category': 'positive'},
    {'query': 'put on some smooth jazz', 'calls': [{'name': 'play_music', 'arguments': {'query': 'smooth jazz'}}], 'category': 'positive'},
    {'query': 'queue up Blinding Lights by The Weeknd', 'calls': [{'name': 'play_music', 'arguments': {'query': 'Blinding Lights by The Weeknd'}}], 'category': 'positive'},
    {'query': 'play some lofi beats', 'calls': [{'name': 'play_music', 'arguments': {'query': 'lofi beats'}}], 'category': 'positive'},
    {'query': 'put on Hotel California by the Eagles', 'calls': [{'name': 'play_music', 'arguments': {'query': 'Hotel California by the Eagles'}}], 'category': 'positive'},
    {'query': 'play Bohemian Rhapsody by Queen', 'calls': [{'name': 'play_music', 'arguments': {'query': 'Bohemian Rhapsody by Queen'}}], 'category': 'positive'},
    {'query': 'set the volume to 40', 'calls': [{'name': 'set_volume', 'arguments': {'level': 40}}], 'category': 'positive'},
    {'query': 'turn the volume up to 85', 'calls': [{'name': 'set_volume', 'arguments': {'level': 85}}], 'category': 'positive'},
    {'query': 'lower the volume to 15', 'calls': [{'name': 'set_volume', 'arguments': {'level': 15}}], 'category': 'positive'},
    {'query': 'set the speaker volume to 60', 'calls': [{'name': 'set_volume', 'arguments': {'level': 60}}], 'category': 'positive'},
    {'query': 'crank the volume up to 95', 'calls': [{'name': 'set_volume', 'arguments': {'level': 95}}], 'category': 'positive'},
    {'query': 'pause the music', 'calls': [{'name': 'pause_media', 'arguments': {}}], 'category': 'positive'},
    {'query': 'hit pause on the song', 'calls': [{'name': 'pause_media', 'arguments': {}}], 'category': 'positive'},
    {'query': 'pause playback while I take this call', 'calls': [{'name': 'pause_media', 'arguments': {}}], 'category': 'positive'},
    {'query': 'resume the music', 'calls': [{'name': 'resume_media', 'arguments': {}}], 'category': 'positive'},
    {'query': 'resume playback where it left off', 'calls': [{'name': 'resume_media', 'arguments': {}}], 'category': 'positive'},
    {'query': 'skip this song', 'calls': [{'name': 'skip_track', 'arguments': {}}], 'category': 'positive'},
    {'query': 'skip to the next track', 'calls': [{'name': 'skip_track', 'arguments': {}}], 'category': 'positive'},
    {'query': 'turn up the volume a little', 'calls': [], 'category': 'missing', 'critical': True},
    {'query': 'play something for me', 'calls': [], 'category': 'missing', 'critical': True},
    {'query': 'turn the music down a bit', 'calls': [], 'category': 'missing', 'critical': True},
    {'query': "play whatever you think I'd like", 'calls': [], 'category': 'missing', 'critical': True},
    {'query': 'put on the podcast Hard Fork', 'calls': [], 'category': 'irrelevant'},
    {'query': 'tune into the radio station Jazz FM', 'calls': [], 'category': 'irrelevant'},
    {'query': 'add this song to my favorites playlist', 'calls': [], 'category': 'irrelevant'},
    {'query': "don't pause the song, I love this part", 'calls': [], 'category': 'negation', 'critical': True},
    {'query': 'do not turn the volume up to 90', 'calls': [], 'category': 'negation', 'critical': True},
    {'query': 'never play Baby Shark on this speaker again', 'calls': [], 'category': 'negation', 'critical': True},
    {'query': 'set the volume to 140', 'calls': [], 'category': 'invalid', 'critical': True},
    {'query': 'turn the volume up to 500', 'calls': [], 'category': 'invalid', 'critical': True},
    {'query': 'set the volume to 55 and play Clair de Lune by Debussy', 'calls': [{'name': 'set_volume', 'arguments': {'level': 55}}, {'name': 'play_music', 'arguments': {'query': 'Clair de Lune by Debussy'}}], 'category': 'parallel'},
    {'query': 'pause the music and turn the volume down to 20', 'calls': [{'name': 'pause_media', 'arguments': {}}, {'name': 'set_volume', 'arguments': {'level': 20}}], 'category': 'parallel'},
]


def run_tests(min_confidence=0.0, verbose=True):
    """Run the frozen acceptance suite against the shipped engine. The default
    scores raw model output; passing e.g. min_confidence=0.4 applies the
    production contract (act on a call only at or above the threshold,
    otherwise treat it as a refusal)."""
    import json

    failures, critical_failures = [], []
    for case in TEST_CASES:
        agent.reset()
        response = agent.complete(case["query"])
        got = response.get("function_calls") or []
        if got and response.get("confidence", 0.0) < min_confidence:
            got = []
        want = case["calls"]
        ok = got == want or sorted(
            json.dumps(c, sort_keys=True) for c in got
        ) == sorted(json.dumps(c, sort_keys=True) for c in want)
        if not ok:
            failures.append(case)
            if case.get("critical"):
                critical_failures.append(case)
            if verbose:
                print(f"FAIL [{case['category']}] {case['query']}")
                print(f"  want {json.dumps(want)}")
                print(f"  got  {json.dumps(got)}")
    passed = len(TEST_CASES) - len(failures)
    print(f"{passed}/{len(TEST_CASES)} passed, {len(critical_failures)} critical failures "
          f"(confidence gate {min_confidence})")
    return passed >= round(0.9 * len(TEST_CASES)) and not critical_failures


if __name__ == "__main__":
    import sys

    sys.exit(0 if run_tests() else 1)
