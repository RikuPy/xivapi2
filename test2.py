import timeit
import gc

# --- 1. Define Data Scenarios ---
# Scenario A: Few optional parameters are set
data_few = {
    "rows": None,                 # Not set
    "fields": ["name", "id"],     # Set
    "after": None,                # Not set
    "limit": 100,                 # Set
    "transient": None,            # Not set
    "language": "en",             # Set
    "schema": None                # Not set
}

# Scenario B: Most optional parameters are set
data_most = {
    "rows": [101, 202, 303, 50],  # Set (needs str conversion)
    "fields": ["name", "id", "description", "value"], # Set
    "after": "some_cursor_string", # Set
    "limit": 50,                  # Set
    "transient": True,            # Set (note: only checked for truthiness)
    "language": "fr",             # Set
    "schema": "v1.2",             # Set
}

scenarios = {
    "Few Params Set": data_few,
    "Most Params Set": data_most,
}

# --- 2. Define Functions for Each Variation ---

# Variation 1: List Comprehension -> Dict Comprehension (Filters None)
def build_params_variation1(data):
    rows = data.get("rows")
    fields = data.get("fields")
    after = data.get("after")
    limit = data.get("limit")
    transient = data.get("transient")
    language = data.get("language")
    schema = data.get("schema")

    # NOTE: This explicitly filters for 'is not None' as per your example
    query_params = {
        key: value
        for key, value in [
            ("rows", ",".join(map(str, rows)) if rows is not None else None), # Check None before join
            ("fields", ",".join(fields) if fields is not None else None), # Check None before join
            ("after", after),
            ("limit", limit),
            ("transient", transient),
            ("language", language),
            ("schema", schema),
        ]
        if value is not None # Filter None values
    }
    return query_params

# Variation 2: Pre-defined Dict (Includes None values - functionally different)
def build_params_variation2_unfiltered(data):
    rows = data.get("rows")
    fields = data.get("fields")
    after = data.get("after")
    limit = data.get("limit")
    transient = data.get("transient")
    language = data.get("language")
    schema = data.get("schema")

    # NOTE: As provided in your prompt, this version *includes* None values.
    # It's NOT functionally equivalent to V1 and V3 unless filtered later.
    query_params = {
        "rows": ",".join(map(str, rows)) if rows is not None else None,
        "fields": ",".join(fields) if fields is not None else None,
        "after": after,
        "limit": limit,
        "transient": transient,
        "language": language,
        "schema": schema,
    }
    # To make it equivalent, you would add:
    query_params = {k: v for k, v in query_params.items() if v is not None}
    return query_params

# Variation 3: Sequential Ifs (Filters Falsy values)
def build_params_variation3(data):
    rows = data.get("rows")
    fields = data.get("fields")
    after = data.get("after")
    limit = data.get("limit")
    transient = data.get("transient")
    language = data.get("language")
    schema = data.get("schema")

    query_params = {}
    # NOTE: This uses implicit truthiness check (if variable:)
    # This means it filters out None, 0, False, empty lists/strings etc.
    if rows:
        query_params["rows"] = ",".join(map(str, rows))
    if fields:
        query_params["fields"] = ",".join(fields)
    if after:
        query_params["after"] = after
    if limit is not None: # Explicit check for limit=0 potentially needed? Using 'is not None' for consistency with V1 filter target
         query_params["limit"] = limit
    # Original code was `if limit:`, which excludes limit=0. Using `is not None` for this benchmark.
    if transient: # Truthiness check is fine here usually
        query_params["transient"] = transient
    if language:
        query_params["language"] = language
    if schema:
        query_params["schema"] = schema
    return query_params


variations = {
    "List+Dict Comp (Filters None)": build_params_variation1,
    "Pre-Dict (Raw - Includes None)": build_params_variation2_unfiltered,
    "Sequential Ifs (Filters Falsy*)": build_params_variation3, # *Filters None for limit here
}

# --- 3. Run Benchmarks ---
number_of_runs = 1_000_000  # Adjust as needed for reasonable timing

print(f"Benchmarking {number_of_runs} executions for each variation...\n")

for scenario_name, current_data in scenarios.items():
    print(f"--- Scenario: {scenario_name} ---")

    # Setup string for timeit - imports the functions and data
    setup_code = f"""
import gc
# Make functions available in timeit's scope
from __main__ import build_params_variation1, build_params_variation2_unfiltered, build_params_variation3
# Define the data for the current scenario
data = {current_data!r} # Use !r for reliable representation
gc.enable() # Ensure GC is enabled before setup runs
"""

    results = {}
    for var_name, var_func in variations.items():
        # Statement to time - calling the specific function
        stmt_code = f"{var_func.__name__}(data)"

        # Run timeit
        # We disable garbage collection during timing for more stable results
        gc.disable()
        time_taken = timeit.timeit(stmt=stmt_code, setup=setup_code, number=number_of_runs, globals=globals())
        gc.enable() # Re-enable GC after timing

        results[var_name] = time_taken
        # Optional: Check results are the same (excluding V2 unfiltered)
        # if var_name != "Pre-Dict (Raw - Includes None)":
        #     res = var_func(current_data)
        #     print(f"      {var_name} Result: {res}")


    # Print sorted results for the scenario
    print("Results (fastest to slowest):")
    for name, time in sorted(results.items(), key=lambda item: item[1]):
         print(f"  {name:<30}: {time:.6f} seconds")

    print("-" * 40 + "\n")


print("Benchmark complete.")
print("\nNotes:")
print(" - Variation 2 (Pre-Dict Raw) is *not* functionally equivalent as it includes None values.")
print(" - Variation 3 (Sequential Ifs) uses truthiness checks generally, but checks `limit is not None` here.")
print(" - Performance can vary based on Python version, hardware, and data complexity.")
print(" - For most applications, readability might be more important than micro-optimization differences.")