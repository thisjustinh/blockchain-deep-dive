class Employee:

    def __init__(self, employee_num, salary, department, supervisor_id):
        self.employee_num = employee_num
        self.salary = salary
        self.department = department
        self.supervisor_id = supervisor_id

    @property
    def mapped(self):
        return {
            'employee_num': self.employee_num,
            'salary': self.salary,
            'department': self.department,
            'supervisor_id': self.supervisor_id
        }
