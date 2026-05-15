from sudachipy import dictionary, tokenizer

sentence = "さくらは有名な芸術家になって展示会を公開しるとき誘って下さい"

tokenizer_obj = dictionary.Dictionary().create()
mode = tokenizer.Tokenizer.SplitMode.C

tokens = tokenizer_obj.tokenize(sentence, mode)

corrected_tokens = []

for token in tokens:
    surface = token.surface()
    normalized = token.normalized_form()

    # Only replace if normalization clearly fixes something
    if surface != normalized and normalized != "*":
        corrected_tokens.append(normalized)
    else:
        corrected_tokens.append(surface)

corrected_sentence = "".join(corrected_tokens)

print("Original:", sentence)
print("Corrected:", corrected_sentence)