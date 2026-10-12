# Armchair integration branch

`dev-armchair` combines six independently based branches. Each feature branch
starts at upstream `81808e195c9a40a01c36b1016ed7e6fbd96a4a3e` so future pull
requests can be reviewed separately.

| Branch | Change |
| --- | --- |
| `feature/llvm24-compat` | Version-gated LLVM APIs, retaining older LLVM support |
| `feature/whole-program-obfuscation` | Optional `-obf-all` selection |
| `fix/string-section-metadata` | Preserve explicitly sectioned strings |
| `fix/embind-signature-metadata` | Preserve Emscripten binding ABI signatures |
| `feature/optional-rdtsc-stretch` | Optional x86 component; automatic omission without the X86 target |
| `feature/persistent-global-strings` | Stable-address, startup-decrypted strings referenced by global tables |

## Pillbox migration

In Pillbox's bootstrap, fetch `https://github.com/Armchair-Software/xollvm.git`
and pin a tested commit from `dev-armchair`. Remove the patch-application loop;
these changes are already in the fork. Keep the LLVM revision, generated-header
setup, libc++ ABI configuration, and AES target settings unchanged. The existing
`Obfuscator` build target, plugin name, and command-line options are preserved.
Use a fresh plugin source/build directory when switching repositories. Update
Pillbox's CI cache key to include the fork revision rather than the removed
patch files.

The WebAssembly-only LLVM configuration automatically disables rdtscStretch,
so no X86 intrinsic headers or extra target generation are needed. For explicit
control, pass `-DOBF_ENABLE_RDTSC_STRETCH=OFF`.

## Regression checks

With a native plugin built against the matching Clang installation:

```sh
python3 utils/test_whole_program.py --compiler clang++ --plugin build/Obfuscator.so
python3 utils/test_string_sections.py --compiler clang++ --plugin build/Obfuscator.so
python3 utils/test_embind_signatures.py --compiler clang++ --plugin build/Obfuscator.so
python3 utils/test_global_strings.py --compiler clang++ --plugin build/Obfuscator.so
```

With emsdk activated and a plugin built against its LLVM/libc++ ABI:

```sh
python3 utils/test_emscripten.py --plugin /path/to/emsdk-plugin/Obfuscator.so \
  --build-dir /tmp/xollvm-emscripten-tests
```

The Emscripten probe covers WASM64, LTO, actual Embind callbacks, embedded
JavaScript, arithmetic obfuscation, all three string ciphers, and retained
catalogue views. Pillbox's browser-loader suite can also use this plugin through
its existing `--plugin` argument.
