// Test Case S1: Array Out of Bounds
// Expected Error: array index out of bounds (runtime warning with sanitizers)
// Student Error Pattern: Off-by-one error
// Difficulty: Intermediate

#include <stdio.h>

int main() {
    int arr[5] = {1, 2, 3, 4, 5};
    int i;
    
    // Classic off-by-one error
    for (i = 0; i <= 5; i++) {  // Should be i < 5
        printf("arr[%d] = %d\n", i, arr[i]);
    }
    
    return 0;
}
