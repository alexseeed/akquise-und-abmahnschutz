// Entry point for `node --test pfade/amazon/tests/`: Node treats a directory argument as a module path and loads this file.
// Dynamic import: works as CommonJS on Node 18 (a static import in a .js file without package.json needs Node >= 22.7).
import("./wiederholen.test.mjs");
import("./abbruch.test.mjs");
