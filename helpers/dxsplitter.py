import re

def SplitSentence(text):
    delimiters = r'([.!?\n])'

    # Use re.split and then merge delimiters with preceding words
    split_result = re.split(delimiters, text)
    merged_result = [split_result[i] + split_result[i + 1] if i + 1 < len(split_result) else split_result[i] 
                    for i in range(0, len(split_result), 2)]
    
    stripped_result = [s.strip() for s in merged_result]
    filtered_result = [item for item in stripped_result if item]

    return filtered_result
