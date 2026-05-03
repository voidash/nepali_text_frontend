"""Tokenization submodule.

Splits text into typed tokens: word | latin | digit | punct |
question_mark | exclamation_mark | other. Each token carries its
source span and a script/language tag so downstream handlers can
route correctly.
"""
