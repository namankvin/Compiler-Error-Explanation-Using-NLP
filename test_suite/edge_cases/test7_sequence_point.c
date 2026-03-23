// Test Case E7: Sequence Point Undefined Behavior
// Expected Error: unsequenced modification / multiple side effects
// Edge Case: Undefined behavior in expressions
// Difficulty: Advanced

#include <stdio.h>

int main() {
    int x = 5;
    
    // Undefined behavior: multiple modifications without sequence point
    int y = x++ + ++x;
    
    printf("x = %d, y = %d\n", x, y);
    
    return 0;
}
