// Test Case B2: Undeclared Variable
// Expected Error: use of undeclared identifier
// Difficulty: Beginner

#include <stdio.h>

int main() {
    count = 5;
    printf("Count = %d\n", count);
    return 0;
}
