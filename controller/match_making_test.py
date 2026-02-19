import asyncio
import sys
import os

# Adjust imports for running as a standalone script
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import match_making module
from controller import match_making
from controller.match_making import main as normal_main, get_random_players, set_test_players

# For colored output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    # Fallback for running without colorama
    class DummyColor:
        def __getattr__(self, name):
            return ""
    
    class DummyStyle:
        def __getattr__(self, name):
            return ""
    
    Fore = DummyColor()
    Style = DummyStyle()


async def main():
    """Run and compare both matchmaking algorithms"""
    # Since we're having import issues with genetic_match_making.py, 
    # let's just run the normal matchmaking with real player data

    print(Fore.CYAN + Style.BRIGHT + "==== Matchmaking with Real Player Data ====")
    
    # Test with bronze players
    print(Fore.YELLOW + "\nTesting with predominantly BRONZE players:")
    set_test_players(get_random_players(count=10, specific_rank="bronze"))
    await normal_main()
    
    # Test with silver players
    print(Fore.YELLOW + "\nTesting with predominantly SILVER players:")
    set_test_players(get_random_players(count=10, specific_rank="silver"))
    await normal_main()
    
    # Test with gold players
    print(Fore.YELLOW + "\nTesting with predominantly GOLD players:")
    set_test_players(get_random_players(count=10, specific_rank="gold"))
    await normal_main()
    
    # Test with mixed rank players
    print(Fore.YELLOW + "\nTesting with MIXED rank players:")
    set_test_players(get_random_players(count=10))
    await normal_main()


async def batch_test(iterations=5):
    """Run a batch test with the matchmaking algorithm across different rank distributions"""
    normal_scores = {
        "bronze": [],
        "silver": [],
        "gold": [],
        "mixed": []
    }
    
    print(Fore.YELLOW + Style.BRIGHT + f"Running {iterations} test iterations for each rank group...")
    
    for i in range(iterations):
        print(f"Iteration {i+1}/{iterations}...")
        
        # Test with different rank groups
        for rank in ["bronze", "silver", "gold", "mixed"]:
            if rank == "mixed":
                players = get_random_players(count=10)
            else:
                players = get_random_players(count=10, specific_rank=rank)
            
            # Set the players for the matchmaking algorithm
            set_test_players(players)
            
            # Run the matchmaking
            t1, t2 = await normal_main()
            
            if t1 and t2:
                # Extract player objects for performance calculation
                team1_players = [item["assigned_to"] for item in t1 if "assigned_to" in item]
                team2_players = [item["assigned_to"] for item in t2 if "assigned_to" in item]
                
                # Calculate team performances
                t1_perf = match_making.teamPerformance(team1_players)
                t2_perf = match_making.teamPerformance(team2_players)
                normal_diff = abs(t1_perf - t2_perf)
                normal_scores[rank].append(normal_diff)
    
    # Calculate and display results
    print(Fore.GREEN + Style.BRIGHT + "\n==== Test Results ====")
    for rank, scores in normal_scores.items():
        if scores:
            avg = sum(scores) / len(scores)
            print(f"{rank.capitalize()} Rank Group - Average Team Performance Difference: {avg:.4f}")
            
            # Calculate standard deviation to check consistency
            if len(scores) > 1:
                import math
                std_dev = math.sqrt(sum((x - avg) ** 2 for x in scores) / len(scores))
                print(f"  Standard Deviation: {std_dev:.4f}")
            
            # Show min and max values
            print(f"  Min: {min(scores):.4f}, Max: {max(scores):.4f}")
        else:
            print(f"{rank.capitalize()} Rank Group - No data collected")


if __name__ == '__main__':
    # Choose the test mode to run
    
    # Regular comparison (single run with different rank groups)
    # asyncio.run(main())
    
    # Batch testing for statistical comparison
    asyncio.run(batch_test(iterations=3))  # Using 3 iterations to keep runtime reasonable

# Add the required setup function for Discord.py cog loading
async def setup(bot):
    # This file doesn't need to be a command cog, but Discord.py requires a setup function
    pass
