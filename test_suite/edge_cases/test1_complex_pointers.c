// Test Case E1: Complex Pointer Declaration
// Expected Error: confusing pointer declaration syntax
// Edge Case: Multiple levels of indirection
// Difficulty: Advanced

#include <stdio.h>

int main() {
    int ***ptr;  // Triple pointer - confusing for beginners
    int val = 42;
    int *p1 = &val;
    int **p2 = &p1;
    ptr = &p2;
    
    printf("Value: %d\n", ***ptr);
    return 0;
}
