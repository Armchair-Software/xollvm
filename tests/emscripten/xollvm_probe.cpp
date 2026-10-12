#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <string_view>
#include <emscripten.h>
#include <emscripten/bind.h>

namespace {

struct entry {
  std::string_view label;
  std::string_view description;
};
entry constexpr catalogue[]{
  {
    .label{"persistent catalogue alpha"},
    .description{"persistent description alpha"},
  },
  {
    .label{"persistent catalogue beta"},
    .description{"persistent description beta"},
  },
  {
    .label{"persistent catalogue gamma"},
    .description{"persistent description gamma"},
  },
};
unsigned int volatile catalogue_index{0};
[[gnu::noinline]] std::string_view lookup() {
  return catalogue[catalogue_index % 3].description;
}
// Access before main, then retain and read the same view after repeated calls.
std::string_view const retained{lookup()};
[[gnu::noinline]] unsigned int catalogue_checksum() {
  unsigned int result{0};
  for(unsigned int i{0}; i != 3; ++i) {
    catalogue_index = i;
    for(char const c : lookup()) result = result * 31U + static_cast<unsigned char>(c);
  }
  for(char const c : retained) result = result * 31U + static_cast<unsigned char>(c);
  return result;
}

[[gnu::noinline]] auto specimen(uint32_t const value)->uint32_t {
  auto result{(value * 1664525U + 1013904223U) ^ (value >> 7U)};
  if(value & 1U) result += value ^ 0xA5'A5'A5'A5U;
  else result ^= value * 17U;
  for(unsigned int index{0}; index < (value & 3U); ++index) result = (result << 3U) ^ (result >> 5U);
  static char constexpr text[]{"obfuscation runtime correctness"};
  return result + static_cast<unsigned char>(text[value % (sizeof(text) - 1)]);
}

// Match asm-dom's pointer/string/val callback, plus a longer ABI signature.
emscripten::val callback(uintptr_t const &pointer, std::string const name, emscripten::val const event) {
  return emscripten::val{pointer == 42 && name.size() == 5 && event["ok"].as<bool>()};
}
int long_callback(int const a, int const b, int const c, int const d, int const e, int const f, int const g) {
  return a + b + c + d + e + f + g;
}
EMSCRIPTEN_BINDINGS(signature_probe) {
  emscripten::function("callback", &callback);
  emscripten::function("long_callback", &long_callback);
}

} // anonymous namespace

auto main()->int {
  uint32_t checksum{0};
  for(uint32_t index{0}; index != 10'000; ++index) {
    checksum = checksum * 31U + specimen(index * 104729U);
  }
  EM_ASM({
    if (!Module.callback(42n, "click", {ok: true})) throw Error("callback failed");
    if (Module.long_callback(1, 2, 3, 4, 5, 6, 7) !== 28) throw Error("long callback failed");
  });
  checksum ^= catalogue_checksum();
  checksum ^= static_cast<unsigned int>(EM_ASM_INT({ return 37; }));
  std::printf("%u\n", checksum);
  return EXIT_SUCCESS;
}
