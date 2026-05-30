{
  outputs = inputs: {
    overlays.default = import ./overlay.nix;
  };
}
