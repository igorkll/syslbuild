uniform sampler2D map;
uniform vec3 color1;
uniform vec3 color2;

varying vec2 vUv;

void main() {
    vec4 tex = texture2D(map, vUv);

    vec3 result = mix(color1, color2, tex.a);

    gl_FragColor = vec4(result, 1.0);

    #include <tonemapping_fragment>
    #include <colorspace_fragment>
}