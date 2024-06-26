import pandas as pd

files_name = ["first_240.csv", "from_240_to_360.csv", "from_360_480.csv", "from_480_to_1000.csv"]
all_df = []
for file in files_name:
    all_df.append(pd.read_csv(file))
df_moves = pd.concat(all_df)

df_moves.to_csv(f"all_processed_moves.csv", encoding='utf-8', index=False)
