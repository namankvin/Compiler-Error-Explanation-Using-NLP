// Test file: Unused return value (CWE-252)
#include <stdio.h>
#include <stdlib.h>

int main() {
    char buffer[100];
    
    // Insecure: ignoring return value of fgets
    fgets(buffer, sizeof(buffer), stdin);
    
    // Insecure: ignoring return value of printf
    printf("You entered: %s\n", buffer);
    
    return 0;
}
