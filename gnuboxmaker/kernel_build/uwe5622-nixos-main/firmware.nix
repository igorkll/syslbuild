{
  stdenvNoCC,
  lib,
  fetchFromGitHub,
  ...
}:
stdenvNoCC.mkDerivation {
  pname = "uwe5622-firmware";
  version = "4050e02";

  compressFirmware = false;
  dontFixup = true;
  dontBuild = true;

  src = fetchFromGitHub {
    owner = "armbian";
    repo = "firmware";
    rev = "4050e02da2dce2b74c97101f7964ecfb962f5aec";
    sha256 = "sha256-wc4xyNtUlONntofWJm8/w0KErJzXKHijOyh9hAYTCoU=";
  };

  installPhase = ''
    mkdir -p $out/lib/firmware
    cp -r uwe5622/* $out/lib/firmware/
  '';

  meta = {
    description = "Firmware for the uwe5622 from armbian.";
    homepage = "https://github.com/armbian/firmware";
    license = lib.licenses.unfreeRedistributableFirmware;
    platforms = [ "aarch64-linux" ];
  };
}
