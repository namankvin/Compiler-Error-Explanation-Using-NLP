// Test Case E6: Strict Aliasing Violation
// Expected Error: dereferencing type-punned pointer
// Edge Case: Type punning through pointers
// Difficulty: Advanced

#include <stdio.h>

int main() {
    float f = 3.14f;
    int *ip;
    
    // Violates strict aliasing rule
    ip = (int *)&f;
    printf("Float as int: %d\n", *ip);
    
    return 0;
}
