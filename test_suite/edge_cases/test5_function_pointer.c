// Test Case E5: Function Pointer Type Mismatch
// Expected Error: incompatible function pointer types
// Edge Case: Callback function signatures
// Difficulty: Advanced

#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

void process(void (*callback)(int, int)) {
    callback(5, 3);
}

int main() {
    // Wrong: add returns int, callback expects void
    process(add);
    
    return 0;
}
