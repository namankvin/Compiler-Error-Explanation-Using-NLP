// Test Case B4: Wrong Format Specifier
// Expected Error: format specifies type but argument has different type
// Difficulty: Beginner

#include <stdio.h>

int main() {
    int age = 25;
    printf("Age: %s\n", age);  // Wrong: %s expects char*, got int
    return 0;
}
