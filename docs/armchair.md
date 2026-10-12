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
python3 utils/test_llvm_compat.py --compiler clang++ --plugin build/Obfuscator.so
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

## Validation of the initial integration

- Native Clang/LLVM 21.1.8: plugin builds with rdtscStretch both ON and OFF;
  global-selection, section metadata, Embind symbol exclusion, and multi-TU
  persistent-string tests pass. Branch-transformation tests pass with both builds.
- Emscripten 6.0.9 / LLVM 24 revision
  `510126255f89d693717c1ce7105b593f995f07c1`: target-limited plugin builds without
  X86 headers; all five WASM64 probe variants and Pillbox's Debug, Release, and
  obfuscated Release browser-loader suites pass.
- The focused native branch-transformation test also passes with LLVM 24.
  That check reused the WASM-targeted plugin and produces target-feature warnings
  from its embedded AES stub; the WASM64 and browser checks use the intended
  target and do not require that cross-target setup.

LLVM 22/23 compatibility paths have not been built in this environment. The
API guards cover the LLVM 23 branch-instruction/pass-policy changes, but an
upstream CI matrix should exercise those installations before merging upstream.
