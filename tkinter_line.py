import tkinter as tk

class LineEditor:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=400, height=400, bg='white')
        self.canvas.pack()
        self.line = None
        self.start_coords = None
        self.end_coords = None
        
        self.canvas.bind('<Button-1>', self.start_line)
        self.canvas.bind('<B1-Motion>', self.update_line)
        self.canvas.bind('<ButtonRelease-1>', self.end_line)
        
    def start_line(self, event):
        self.start_coords = (event.x, event.y)
        self.line = self.canvas.create_line(self.start_coords[0], self.start_coords[1],
                                             self.start_coords[0], self.start_coords[1])
        
    def update_line(self, event):
        if self.line:
            self.end_coords = (event.x, event.y)
            self.canvas.coords(self.line, self.start_coords[0], self.start_coords[1],
                                self.end_coords[0], self.end_coords[1])
            
    def end_line(self, event):
        self.end_coords = (event.x, event.y)
        self.canvas.coords(self.line, self.start_coords[0], self.start_coords[1],
                            self.end_coords[0], self.end_coords[1])
        self.draw_weights()
        
    def draw_weights(self):
        dx = self.end_coords[0] - self.start_coords[0]
        dy = self.end_coords[1] - self.start_coords[1]
        slope = dy / dx
        
        weights = [slope * i for i in range(10)]
        print(weights)
        
root = tk.Tk()
editor = LineEditor(root)
root.mainloop()
