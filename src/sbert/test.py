from modeling import get_model

model = get_model()
print(model.state_dict().keys())