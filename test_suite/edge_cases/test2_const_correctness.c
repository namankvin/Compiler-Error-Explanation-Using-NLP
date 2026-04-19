// Test Case E2: Const Correctness Violation
// Expected Error: discards const qualifier
// Edge Case: Const pointer conversion
// Difficulty: Advanced

#include <stdio.h>

void modify_string(char *str) {
    str[0] = 'H';
}

int main() {
    const char *message = "Hello";
    
    // Error: passing const char* to char* parameter
    modify_string((char *)message);  // Dangerous cast
    
    return 0;
}
