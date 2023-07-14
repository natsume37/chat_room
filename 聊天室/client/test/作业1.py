# coding:utf-8
# USER: 冷不丁
# @FILE_NAME: 作业1
# @TIME: 2023/7/11 12:27
import random

employeesID_list = []
for i in range(1, 301):
    employeesID_list.append(i)


def chock_prize(prize_grade, times):
    for i in range(times):
        random_c = random.randint(1, 300)
        try:
            prize_grade.append(employeesID_list[random_c])
        except:
            continue
        employeesID_list.pop(random_c)


if __name__ == '__main__':
    one_grade = []
    two_grade = []
    three_grade = []
    chock_prize(one_grade, 3)
    chock_prize(two_grade, 6)
    chock_prize(three_grade, 30)
    print(f'三等奖获得者ID：{one_grade}')
    print(f'二等奖获得者ID：{two_grade}')
    print(f'一等奖获得者ID：{three_grade}')
