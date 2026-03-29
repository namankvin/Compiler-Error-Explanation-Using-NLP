// Test Case S5: Signed/Unsigned Comparison
// Expected Error: comparison of integers of different signs
// Student Error Pattern: Mixing int and size_t
// Difficulty: Intermediate

#include <stdio.h>
#include <string.h>

int main() {
    char str[] = "Hello";
    int i;
    
    // Bug: comparing signed int with unsigned size_t
    for (i = 0; i < strlen(str); i++) {
        printf("%c ", str[i]);
    }
    printf("\n");
    
    // Another common pattern - negative index check that fails
    int index = -1;
    if (index < strlen(str)) {  // Always true! -1 becomes large positive
        printf("Accessing str[%d]\n", index);
        printf("%c\n", str[index]);  // Undefined behavior
    }
    
    return 0;
}
