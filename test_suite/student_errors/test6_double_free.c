// Test Case S6: Double Free
// Expected Error: potential double free (detected by static analysis)
// Student Error Pattern: Freeing memory twice
// Difficulty: Intermediate

#include <stdio.h>
#include <stdlib.h>

int main() {
    int *ptr = malloc(sizeof(int) * 10);
    
    if (ptr == NULL) {
        return 1;
    }
    
    *ptr = 42;
    printf("Value: %d\n", *ptr);
    
    free(ptr);
    // Student forgot they already freed
    free(ptr);  // Double free!
    
    return 0;
}
