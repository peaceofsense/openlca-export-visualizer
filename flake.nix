{
  description = "OpenLCA impact assessment visualization";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python312;
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          (python.withPackages (ps: with ps; [
            streamlit
            pandas
            numpy
            matplotlib
            scienceplots
            openpyxl
          ]))
        ];
      };
    };
}
