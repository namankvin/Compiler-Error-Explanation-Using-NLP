// Test file: Format string mismatch (CWE-134)
#include <stdio.h>

int main() {
    int value = 42;
    size_t count = 100;
    
    // Insecure: wrong format specifier for size_t
    printf("Count: %d\n", count);  // Should be %zu
    
    // Insecure: wrong format specifier 
    printf("Value: %ld\n", value);  // Should be %d
    
    return 0;
}
