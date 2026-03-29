// Test Case E4: Enum Type Mismatch
// Expected Error: implicit conversion from enum to int / comparison mismatch
// Edge Case: Enum type safety
// Difficulty: Advanced

#include <stdio.h>

typedef enum {
    RED,
    GREEN,
    BLUE
} Color;

typedef enum {
    SMALL,
    MEDIUM,
    LARGE
} Size;

int main() {
    Color c = RED;
    Size s = SMALL;
    
    // Comparing different enum types - logically wrong but compiles
    if (c == s) {
        printf("Same value\n");
    }
    
    // Assigning int to enum
    c = 100;  // Valid but dangerous
    
    return 0;
}
