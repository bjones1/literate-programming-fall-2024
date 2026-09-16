"""A simple number guessing game."""

secret_number = 7

guess = int(input("Guess a number from 1 to 10: "))

if guess == secret_number:
    print("Correct!")
elif guess < secret_number:
    print("Too low!")
else:
    print("Too high!")