{
  description = "HackMTY 2026 - Capital One challenge dev environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          # Control de versiones
          git
          gh

          # Node / JS (frontend, APIs rápidas)
          nodejs_22
          pnpm
          yarn

          # Python (scripts, datos, ML rápido)
          python312
          python312Packages.pip
          poetry
          uv

          # Java (stack típico de fintech/banca, incluido Capital One)
          jdk21
          maven
          gradle

          # Go / Rust por si el reto pide algo de bajo nivel o alto performance
          go
          rustc
          cargo

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
          echo "Entorno HackMTY listo."
          echo "Node: $(node -v) | Python: $(python3 --version) | Java: $(java -version 2>&1 | head -n1)"
        '';
      };
    };
}
