# Google Python Style Guide Summary

This document summarizes key rules and best practices from the Google Python
Style Guide.

## Python language rules

- Run `pylint` or the repo's configured linting tools to catch bugs and style
  issues.
- Use `import x` for packages and modules. Use `from x import y` only when
  `y` is a submodule or the import is otherwise justified.
- Use built-in exception classes. Do not use bare `except:` clauses.
- Avoid mutable global state.
- Use type annotations for public APIs.

## Python style rules

- Keep line length reasonable and match the project's configured formatter.
- Use 4 spaces per indentation level.
- Use two blank lines between top-level definitions.
- Use triple double quotes for docstrings.
- Every public module, function, class, and method should have a docstring.
- Use f-strings for formatting.
- Keep imports grouped and ordered: standard library, third-party, local.

## Naming

- Use `snake_case` for modules, functions, methods, and variables.
- Use `PascalCase` for classes.
- Use `ALL_CAPS_WITH_UNDERSCORES` for constants.

## Main entry points

- Use a `main()` function for executable modules.
- Guard script execution with `if __name__ == "__main__":`.
