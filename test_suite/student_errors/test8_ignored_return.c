// Test Case S8: Return Value Ignored
// Expected Error: unused return value
// Student Error Pattern: Not checking function return values
// Difficulty: Intermediate

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    FILE *file = fopen("nonexistent.txt", "r");
    // Student didn't check if file opened successfully
    
    char buffer[100];
    fgets(buffer, sizeof(buffer), file);  // Using NULL file pointer
    
    printf("Content: %s\n", buffer);
    
    fclose(file);
    return 0;
}
