{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Control de versiones
    git
    gh

    # Node / JS
    nodejs_22
    pnpm
    yarn

    # Python
    python312
    python312Packages.pip
    poetry
    uv

    # Java (stack típico de fintech)
    jdk21
    maven
    gradle

    # Contenedores
    docker
    docker-compose

    # Bases de datos y clientes
    postgresql
    sqlite
    redis

    # Cloud y pruebas de API
    awscli2
    httpie
    jq
    curl

    # Utilidades generales
    ripgrep
    fd
    tree
    unzip
  ];

  shellHook = ''
    echo "🚀 Entorno HackMTY listo."
    echo "Node: $(node -v) | Python: $(python3 --version) | Java: $(java -version 2>&1 | head -n1)"
  '';
}
