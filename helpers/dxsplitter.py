import re

def SplitSentence(text):
    """
    Splits a text into sentences while keeping sentence-ending punctuation attached.
    
    Args:
        text (str): The input text to split.
    
    Returns:
        list: A list of sentences with punctuation attached.
    """
    # Regex pattern to match sentence-ending punctuation: "..." | "!!!" | "?!" | "." | "!" | "?"
    pattern = r'(\.{3}|[.!?]+)'

    # Split text while keeping punctuation in the result
    split_sentences = re.split(pattern, text)

    # Merge sentences with their punctuation
    sentences = [
        (split_sentences[i] + split_sentences[i + 1]).strip() if i + 1 < len(split_sentences) 
        else split_sentences[i].strip()
        for i in range(0, len(split_sentences), 2)
    ]

    # Filter out empty strings (only needed once)
    return [s for s in sentences if s]
