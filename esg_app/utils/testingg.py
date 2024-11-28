
import pandas as pd
import numpy as np
df = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
                   columns=['a', 'b', 'c'])
num_threads = 2

chunk_size = len(df) // num_threads
df_chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
    
    # If there are any remaining rows, add them to the last chunk
if len(df_chunks) > num_threads:
    df_chunks[-2] = pd.concat([df_chunks[-2], df_chunks[-1]])
    df_chunks.pop()

for chunk in df_chunks:
    print("Chunk")
    print(chunk)

data = pd.read_csv('esg_app/api/data/SP500.csv')
print("Length:", len(data))