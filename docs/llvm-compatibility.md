# LLVM API compatibility

`LLVMCompat.h` isolates the LLVM 23/24 branch-instruction split and explicit pass
policy from the LLVM 21--22 API. Existing `isRequired()` overrides are retained.
Instruction insertion uses iterators, supported by both APIs.

Build the plugin against each LLVM installation separately; plugin binaries are
not ABI-compatible across LLVM versions. Exercise both conditional and
unconditional branches through arithmetic, flattening and VM regression cases.
The project's normal runtime runner remains the regression entry point.
