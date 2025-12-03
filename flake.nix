{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    # Ancient version of nixpkgs with support for Python 3.6
    oldNixpkgs.url = "github:NixOS/nixpkgs/nixos-21.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      oldNixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        oldPkgs = import oldNixpkgs {
          inherit system;
        };
        pkgs = import nixpkgs {
          inherit system;
        };
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = [
            oldPkgs.pipenv
            oldPkgs.python36
          ];
        };
        formatter = pkgs.nixfmt-tree;
      }
    );
}
