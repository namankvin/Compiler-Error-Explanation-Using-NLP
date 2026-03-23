// Test file: Sign comparison issue (CWE-190)
#include <stdio.h>

int main() {
    int arr[] = {1, 2, 3, 4, 5};
    int len = sizeof(arr) / sizeof(arr[0]);
    
    // Insecure: mixing signed and unsigned in comparison
    for (int i = 0; i < len - 1; i++) {
        printf("%d ", arr[i]);
    }
    
    // Tautological: unsigned can never be negative
    if (len >= 0) {
        printf("Length is non-negative\n");
    }
    
    return 0;
}
