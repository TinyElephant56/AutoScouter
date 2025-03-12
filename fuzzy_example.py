from rapidfuzz import process, fuzz

# What your text found in a robot bbox - wont be exact match... 
# this is what I get from the bottom right in example.jpg, excluding the scoreboard (I also get 9772)
search_string = "180160"

# Robots that are actually in the match (probably you get these from tba - https://github.com/TBA-API/tba-api-client-python)
options = [
    "8060",
    "9772",
    "4"
]

# Find the best match
# This will return a list of tuples (match, score, index)
matches = process.extractOne(
    search_string,    # String to match
    options,         # List of choices
    scorer=fuzz.ratio  # Scoring function to use (try WRation too if you want)
)

print(f"Search string: {search_string}")
print(f"Best match: {matches[0]}")  # The matched string
print(f"Score: {matches[1]}")       # Score from 0-100
print(f"Index: {matches[2]}")       # Index in the original list

# You can also get all matches sorted by score
all_matches = process.extract(
    search_string,
    options,
    scorer=fuzz.ratio,
    limit=None  # Return all matches
)

print("\nAll matches sorted by score:")
for match, score, index in all_matches:
    print(f"Match: {match}, Score: {score}, Index: {index}")

# at this point you could pick the highest, as long as it is above a threshold
MATCH_THRESHOLD = 60  # not sure where this needs to lie

# Get the best match and check if it's above threshold
best_match, best_score, best_index = matches

if best_score >= MATCH_THRESHOLD:
    print(f"\nFound reliable match: {best_match} (score: {best_score})")
else:
    print(f"\nNo reliable match found. Best candidate {best_match} with score {best_score} below threshold {MATCH_THRESHOLD}")
