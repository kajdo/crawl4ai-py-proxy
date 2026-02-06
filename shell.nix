{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python3
    uv
  ];

  shellHook = ''
    # Set up virtual environment with uv if it doesn't exist
    if [ ! -d ".venv" ]; then
      uv venv
    fi

    # Activate the virtual environment
    source .venv/bin/activate

    # Install requirements if requirements.txt exists and .venv is new
    if [ -f "requirements.txt" ] && [ ! -f ".venv/.initialized" ]; then
      uv pip install -r requirements.txt
      touch .venv/.initialized
    fi
  '';
}