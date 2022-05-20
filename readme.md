# Can Lib

## Install

```
pip install git+https://github.com/eagletrt/canlib.git#egg=canlib
```

## Command Completion

Completion is only available if a script is installed and invoked through an
entry point, not through the python command. Once the executable is installed,
calling it with a special environment variable will put Click in completion mode.

### Bash

Add this to `~/.bashrc`:

```
eval "$(_CANLIB_COMPLETE=bash_source canlib)"
```

### Zsh

Add this to `~/.zshrc`:

```
eval "$(_CANLIB_COMPLETE=zsh_source canlib)"
```

### Fish

Add this to `~/.config/fish/completions/canlib.fish`:

```
eval (env _CANLIB_COMPLETE=fish_source canlib)
```
