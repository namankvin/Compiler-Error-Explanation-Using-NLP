// Test Case B3: Type Mismatch
// Expected Error: incompatible integer/pointer types
// Difficulty: Beginner

#include <stdio.h>

int main() {
    int num = 42;
    char *str = num;  // Wrong: assigning int to char pointer
    printf("Value: %s\n", str);
    return 0;
}
