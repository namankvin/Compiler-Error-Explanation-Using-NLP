// Test file: Implicit declaration (CWE-434)
// Missing #include <stdlib.h>

int main() {
    // Insecure: calling malloc without declaration
    int *ptr = malloc(100);
    
    if (ptr != NULL) {
        *ptr = 42;
        free(ptr);
    }
    
    return 0;
}
