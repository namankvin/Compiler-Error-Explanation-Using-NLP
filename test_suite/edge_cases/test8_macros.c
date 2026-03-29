// Test Case E8: Macro Expansion Issues
// Expected Error: multiple evaluation / operator precedence
// Edge Case: Macro side effects
// Difficulty: Advanced

#include <stdio.h>

#define SQUARE(x) x * x
#define MAX(a, b) a > b ? a : b

int main() {
    int result;
    
    // Bug: expands to 3 + 3 * 3 + 3 = 15, not 36
    result = SQUARE(3 + 3);
    printf("SQUARE(3+3) = %d\n", result);
    
    // Bug: i++ evaluated twice
    int i = 5;
    result = MAX(i++, 3);
    printf("MAX result: %d, i: %d\n", result, i);
    
    return 0;
}
