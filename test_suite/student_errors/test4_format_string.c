// Test Case S4: Format String Vulnerability
// Expected Error: format string is not a string literal
// Student Error Pattern: Using user input as format string
// Difficulty: Intermediate

#include <stdio.h>

int main() {
    char user_input[100];
    
    printf("Enter text: ");
    fgets(user_input, sizeof(user_input), stdin);
    
    // DANGEROUS: User input as format string
    printf(user_input);
    
    return 0;
}
