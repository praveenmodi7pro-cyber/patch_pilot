"""Authentication service with intentional syntax error."""

def verify_token(token)
    # BUG: Missing colon on line above causes Python SyntaxError
    if not token:
        return False
    return token.startswith("tok_")

