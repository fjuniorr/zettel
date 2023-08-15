def unpack_fzf_prompt(prompt):
    if not prompt:
        return (None, None)
    elif len(prompt.split('\n')) == 1:
        return (prompt, None)
    else:
        return prompt.split('\n')