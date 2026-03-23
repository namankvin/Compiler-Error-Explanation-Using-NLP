// Test Case S7: Uninitialized Variable
// Expected Error: variable may be used uninitialized
// Student Error Pattern: Using variable before initialization
// Difficulty: Intermediate

#include <stdio.h>

int main() {
    int result;
    int divisor = 0;
    
    // Conditional initialization - may not execute
    if (divisor != 0) {
        result = 100 / divisor;
    }
    
    // Bug: result may be uninitialized here
    printf("Result: %d\n", result);
    
    return 0;
}
