// Test Case S2: Unchecked malloc Return
// Expected Error: unused return value / potential null dereference
// Student Error Pattern: Not checking allocation success
// Difficulty: Intermediate

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char *buffer = malloc(100);
    // Student forgot to check if malloc succeeded
    
    strcpy(buffer, "Hello World");
    printf("Buffer: %s\n", buffer);
    
    free(buffer);
    return 0;
}
